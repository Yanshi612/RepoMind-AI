function RepoCard(){

return(

<div>


<div className="bg-gray-900 p-8 rounded-2xl">


<h2 className="text-3xl font-bold">
facebook/react
</h2>


<p className="text-gray-400 mt-2">
Open Source Repository Analysis
</p>


</div>



<div className="grid grid-cols-3 gap-6 mt-8">



<div className="bg-gray-900 p-6 rounded-xl">

<h3>
Security
</h3>

<p className="text-green-400 text-3xl">
88%
</p>

</div>



<div className="bg-gray-900 p-6 rounded-xl">

<h3>
Code Quality
</h3>

<p className="text-blue-400 text-3xl">
90%
</p>

</div>




<div className="bg-gray-900 p-6 rounded-xl">

<h3>
Health Score
</h3>

<p className="text-purple-400 text-3xl">
92%
</p>

</div>



</div>




<div className="bg-gray-900 mt-8 p-8 rounded-xl">


<h2 className="text-2xl font-bold">
AI Findings
</h2>


<ul className="mt-5 space-y-3">


<li>
⚠️ 3 unused dependencies found
</li>


<li>
⚠️ Possible SQL injection risk detected
</li>


<li>
✅ Authentication structure is good
</li>


</ul>


</div>


</div>


)

}


export default RepoCard;