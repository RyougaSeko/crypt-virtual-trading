alert("hello")
value = 10000000

setInterval(myfnc, 1000)
 
 function myfnc(){

//  document.addEventListener('DOMContentLoaded', function() {

            $.ajax({
                url: 'https://api.coincap.io/v2/assets', //アクセスするURL
                type: 'get',   //post or get
                cache: false,        //cacheを使うか使わないかを設定
                dataType:'json',     //data type script・xmlDocument・jsonなど
            })
            .done(function(response) { 
                //通信成功時の処理
                //成功したとき実行したいスクリプトを記載
                //responseはjsonオブジェクト
                console.log(response)
                // document.querySelector('h2').innerHTML = response.data[0]["id"]
                Example(response)
            })
            .fail(function(xhr) {  
                //通信失敗時の処理
                //失敗したときに実行したいスクリプトを記載
            })
            .always(function(xhr, msg) { 
                //通信完了時の処理
                //結果に関わらず実行したいスクリプトを記載
            });   

                // sleep(10000);
    // })

}


function Example(jsonObj){
    // const data = jsonObj.data[0]["id"];
    const data2 = jsonObj.data[0]["priceUsd"];
    const obj = document.getElementById('btc_price')
    obj.innerHTML = data2;
    // document.querySelector('h3').innerHTML = data2;

    if (value >= data2) {
        //色をかえる
        $(function(){
            //色を指定するのはどちらでもできる
            obj.style.color = "#00FF00"
            // $("h3").css("color", "#00FF00");
        
        });
    } else if (value < data2) {
       //色をかえる
       $(function(){
        //色を指定するのはどちらでもできる
        obj.style.color = "#ED1A3D"
        // $("h3").css("color", "#ED1A3D");
    
    });

    } 
      value = data2
   }

